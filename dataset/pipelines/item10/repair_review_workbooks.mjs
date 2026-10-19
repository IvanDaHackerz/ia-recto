import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
const runtimeRoot=process.env.CODEX_ARTIFACT_NODE_ROOT||'C:/Users/gdhsb/.cache/codex-runtimes/codex-primary-runtime/dependencies/node';
const runtimeRequire=createRequire(`${runtimeRoot}/artifact-loader.cjs`);
const { FileBlob, SpreadsheetFile }=await import(runtimeRequire.resolve('@oai/artifact-tool'));
const root='C:/IA';
const preview=`${root}/tmp/item10_workbook_build/cleanup-previews`;
await fs.mkdir(preview,{recursive:true});
const mode=process.argv[2]||'preview';
if(mode==='preview') {
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/outputs/item10-review-workbooks/EMBOLTORIO_item10_reviewer_5.xlsx`));
  for(const [sheetName,range,name] of [['Review Queue','H14:Q17','before-review'],['Progress','A1:B13','before-progress']]) {
    const blob=await wb.render({sheetName,range,scale:1.5});
    await fs.writeFile(`${preview}/${name}.png`,new Uint8Array(await blob.arrayBuffer()));
  }
  console.log('Saved original workbook previews.');
}
if(mode==='verify_render') {
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/outputs/item10-review-cleaned/EMBOLTORIO_item10_reviewer_5.xlsx`));
  console.log((await wb.inspect({kind:'table',range:'Progress!A5:B13',include:'values,formulas',tableMaxRows:9,tableMaxCols:2,maxChars:2500})).ndjson);
  console.log(wb.help('render',{include:'examples,notes',maxChars:3500}).ndjson);
  for(const [sheetName,range,name] of [['Progress','A1:B13','reopened-progress'],['Review Queue','A1:G10','reopened-review']]) {
    const blob=await wb.render({sheetName,range,scale:1.5});
    await fs.writeFile(`${preview}/${name}.png`,new Uint8Array(await blob.arrayBuffer()));
  }
}
if(mode==='repair') {
  const manifest=JSON.parse(await fs.readFile(`${root}/dataset/processed/item10/reviewed_v1.0.0/dataset_manifest.json`,'utf8'));
  if(manifest.status==='frozen_reviewed_seed')throw new Error('This version is frozen; create a new version instead of overwriting its cleaned workbooks.');
  const payload=JSON.parse(await fs.readFile(`${root}/tmp/item10_workbook_build/cleanup_payload.json`,'utf8'));
  const output=`${root}/outputs/item10-review-cleaned`;
  await fs.mkdir(output,{recursive:true});
  const checks=[];
  function rowCheck(r) {
    const rules=[
      [`$O${r}=""`,'Set reviewer name'],
      [`NOT(OR($H${r}="Keep as written",$H${r}="Revise wording",$H${r}="Reject wording"))`,'Choose wording decision'],
      [`NOT(OR($J${r}="Labels correct",$J${r}="Change labels",$J${r}="Unsure"))`,'Choose label decision'],
      [`NOT(OR($N${r}="Approved",$N${r}="Revised approved",$N${r}="Needs group discussion",$N${r}="Rejected"))`,'Choose outcome'],
      [`AND($H${r}="Revise wording",$I${r}="")`,'Add revised question'],
      [`AND($H${r}<>"Revise wording",$I${r}<>"")`,'Clear unused revision'],
      [`AND($H${r}="Reject wording",$N${r}<>"Rejected")`,'Use Rejected outcome'],
      [`AND($J${r}="Change labels",OR(NOT(OR($K${r}="labor",$K${r}="consumer",$K${r}="mixed",$K${r}="out_of_scope")),NOT(OR($L${r}="fully_supported",$L${r}="partially_supported",$L${r}="unsupported"))))`,'Add corrected labels'],
      [`AND($J${r}<>"Change labels",OR($K${r}<>"",$L${r}<>"",$M${r}<>""))`,'Clear unused corrections'],
      [`AND($J${r}="Change labels",NOT(OR(AND(OR($K${r}="labor",$K${r}="consumer"),$L${r}="fully_supported"),AND($K${r}="mixed",OR($L${r}="fully_supported",$L${r}="partially_supported")),AND($K${r}="out_of_scope",$L${r}="unsupported"))))`,'Check label and scope'],
      [`AND($J${r}="Unsure",$N${r}<>"Needs group discussion")`,'Use group discussion'],
      [`AND($N${r}="Approved",OR($H${r}="Revise wording",$J${r}="Change labels"))`,'Use Revised approved'],
      [`AND($N${r}="Revised approved",$H${r}<>"Revise wording",$J${r}<>"Change labels")`,'Mark what changed'],
      [`AND(OR($N${r}="Needs group discussion",$N${r}="Rejected"),$P${r}="",$M${r}="")`,'Add decision note'],
    ];
    return '='+rules.reduceRight((tail,[condition,msg])=>`IF(${condition},"${msg}",${tail})`,'"Ready"');
  }
  for(const batch of payload.workbooks) {
    const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/outputs/item10-review-workbooks/${batch.file}`));
    const q=wb.worksheets.getItem('Review Queue');
    for(const item of batch.rows) {
      for(const col of ['C','D','H','I','J','K','L','M','N','P']) {
        if(item.cells[col]!==item.original_cells[col])q.getRange(`${col}${item.row}`).values=[[item.cells[col]||null]];
      }
    }
    const end=5+batch.rows.length;
    q.getRange(`Q6:Q${end}`).formulas=batch.rows.map(item=>[rowCheck(item.row)]);
    q.getRange('A3').values=[[`${batch.rows.length} assigned questions. Cleaned copy. Consolidation decisions are recorded in Notes and the accompanying change log.`]];
    // Keep identifiers and wrapped review text readable in the cleaned copies.
    q.getRange(`B5:B${end}`).format.columnWidthPx=185;
    q.getRange(`D5:D${end}`).format.columnWidthPx=80;
    q.getRange(`M5:M${end}`).format.columnWidthPx=300;
    q.getRange(`P5:P${end}`).format.columnWidthPx=300;
    q.getRange('A5:Q5').format.rowHeightPx=46;
    function lines(text,capacity) {
      return String(text||'').split('\n').reduce((n,line)=>{
        let count=1,length=0;
        for(const word of line.split(/\s+/)) {
          if(length+word.length+1>capacity){count++;length=word.length;}
          else length+=word.length+1;
        }
        return n+count;
      },0);
    }
    for(const item of batch.rows) {
      const needed=Math.max(lines(item.cells.C,42),lines(item.cells.G,30),lines(item.cells.I,34),lines(item.cells.M,40),lines(item.cells.P,40));
      q.getRange(`A${item.row}:Q${item.row}`).format.rowHeightPx=Math.max(76,needed*16+16);
    }
    wb.worksheets.getItem('Progress').getRange('A3').values=[['Counts update when the Review Queue recalculates.']];
    const ref=wb.worksheets.getItem('Referrals');
    const refIds=ref.getRange('A6:A30').values;
    for(const updated of payload.referrals.filter(r=>['REF_DMW','REF_PAO'].includes(r.referral_id))) {
      const index=refIds.findIndex(row=>row[0]===updated.referral_id);
      if(index<0)throw new Error('Missing referral '+updated.referral_id);
      ref.getRange(`D${index+6}`).values=[[updated.when_to_use]];
      ref.getRange(`A${index+6}:F${index+6}`).format.rowHeightPx=100;
    }
    wb.recalculate();
    const statuses=q.getRange(`Q6:Q${end}`).values.flat();
    if(statuses.some(x=>x!=='Ready'))throw new Error(`${batch.file}: ${JSON.stringify(statuses.filter(x=>x!=='Ready'))}`);
    const progress=wb.worksheets.getItem('Progress').getRange('B7:B11').values.flat();
    if(progress[0]!==batch.rows.length||progress[1]!==batch.rows.length||progress[2]!==0)throw new Error(`${batch.file}: progress count mismatch`);
    const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},maxChars:2500});
    if(!errors.ndjson.includes('matched 0 entries'))throw new Error(errors.ndjson);
    const testRow=batch.rows.find(x=>x.cells.N==='Revised approved');
    if(testRow) {
      const range=q.getRange(`N${testRow.row}`);
      range.values=[['Approved']];
      const warning=q.getRange(`Q${testRow.row}`).values[0][0];
      if(warning!=='Use Revised approved')throw new Error('Completion check failed to detect a conflicting outcome: '+warning);
      range.values=[['Revised approved']];
      wb.recalculate();
      if(q.getRange(`Q${testRow.row}`).values[0][0]!=='Ready')throw new Error('Completion check did not recover');
    }
    const file=await SpreadsheetFile.exportXlsx(wb);
    await file.save(`${output}/${batch.file}`);
    // Verify the saved file and render from the reopened workbook. Rendering
    // after a large mutation batch produced empty previews in this runtime.
    const reopened=await SpreadsheetFile.importXlsx(await FileBlob.load(`${output}/${batch.file}`));
    const progressBlob=await reopened.render({sheetName:'Progress',range:'A1:B13',scale:1.5});
    await fs.writeFile(`${preview}/${batch.reviewer}-progress.png`,new Uint8Array(await progressBlob.arrayBuffer()));
    const detailBlob=await reopened.render({sheetName:'Review Queue',range:'A1:G8',scale:1.5});
    await fs.writeFile(`${preview}/${batch.reviewer}-review.png`,new Uint8Array(await detailBlob.arrayBuffer()));
    checks.push({file:batch.file,ready:statuses.length,rejected:progress[4],errors:0,formula_conflict_probe:'passed'});
    console.log(JSON.stringify(checks.at(-1)));
  }
  await fs.writeFile(`${output}/workbook_checks.json`,JSON.stringify(checks,null,2)+'\n');
}
