"""Read-only availability/contact audit; HTTP success is not legal currentness."""
from __future__ import annotations
import argparse,concurrent.futures,datetime,hashlib,json,re,urllib.request
from pathlib import Path
from common import ROOT,csvrows,save

def fetch(job):
    result={**job,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'legal_currentness_certified':False,'contact_details_verified':False}
    try:
        request=urllib.request.Request(job['url'],headers={'User-Agent':'Mozilla/5.0 (public-source research)'})
        with urllib.request.urlopen(request,timeout=15) as response:
            body=response.read(4_000_000)
            result.update(http_status=response.status,final_url=response.url,
                sha256=hashlib.sha256(body).hexdigest(),bytes_read=len(body))
            text=re.sub(r'<[^>]+>',' ',body.decode('utf-8','replace'))
            result['contact_literal_matches']={key:bool(value and value.casefold() in text.casefold())
                for key,value in job.get('contacts',{}).items()}
            result['status']='accessible_requires_content_review'
    except Exception as error:
        result.update(status='access_failed_requires_official_alternative',error=str(error)[:240])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Use a new audit output')
    jobs=[{'kind':'legal_source','id':r['document_id'],'url':r['official_source_url']}
          for r in csvrows(ROOT/'dataset/canonical_sources/manifests/canonical_documents.csv')]
    jobs += [{'kind':'referral','id':r['referral_id'],'url':r['verification_source_url'],
              'contacts':{k:r[k] for k in ['email','phone','office_address']}}
             for r in csvrows(ROOT/'dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(fetch,jobs))
    save(a.output,{'role':'Automated public URL and literal-contact audit, not legal or human approval',
        'original_metadata_modified':False,'sources':results,
        'accessible':sum(r['status']=='accessible_requires_content_review' for r in results),
        'total':len(results),'all_legal_status_dates_remain_unchanged':True})
    print(json.dumps({'accessible':sum(r['status']=='accessible_requires_content_review' for r in results),'total':len(results)}))
if __name__=='__main__':main()
