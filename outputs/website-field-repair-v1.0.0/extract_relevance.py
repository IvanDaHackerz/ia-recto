"""One-time source refactor: share pure topical matching with the application."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'dataset/pipelines/item11/retrieval.py'
t=p.read_text(encoding='utf-8')
vocabulary=t[t.index('STOP=set('):t.index('def ranking_expansion(')]
features=t[t.index('# Transparent, taxonomy-level'):t.index('class LegalRetriever:')]
target=p.with_name('query_relevance.py')
if target.exists():raise ValueError('Already extracted')
target.write_text('"""Pure local query/source concepts; no models, IDs, network or legal claims."""\nimport re,unicodedata\n\n'+vocabulary+features,encoding='utf-8')
t=t.replace(vocabulary,'from query_relevance import tokens,query_facets,source_relevance,relevant_excerpt\n\n')
t=t.replace(features,'')
p.write_text(t,encoding='utf-8')
