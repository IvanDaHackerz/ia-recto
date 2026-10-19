"""Expose only individually confirmed fields from a disclosed refresh artifact."""
import argparse,json
from pathlib import Path
def lookup(path,referral_id):
    rows=json.loads(Path(path).read_text(encoding='utf-8'))
    row=next(r for r in rows if r['referral_id']==referral_id)
    return {'referral_id':referral_id,'agency':row['agency'],'service':row['service'],
        'contact':row['confirmed_fields'],'verification':row['field_verification'],
        'official_information_url':row['verification_source_url'],'note':row['note'],
        'contact_verification_complete':row['complete_contact_verification'],
        'unverified_fields_withheld':row['unverified_fields_withheld'],
        'deployment_allowed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--referral-id',required=True);a=p.parse_args()
    print(json.dumps(lookup(a.directory,a.referral_id),ensure_ascii=False,indent=2))
