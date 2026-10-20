import type { Domain, Scope } from "../data/answers";
const LABELS: Record<Domain, string> = { labor: "Labor", consumer: "Consumer", mixed: "Multiple topics", out_of_scope: "Outside supported topics" };
const SCOPES: Record<Scope, string> = { fully_supported: "Within topic scope", partially_supported: "Partly within scope", unsupported: "Outside scope" };
export function DomainTag({ domain, scope }: { domain: Domain; scope?: Scope }) {
  return <p className="domain-label">{LABELS[domain]}{scope && <span className="scope-label">{SCOPES[scope]}</span>}</p>;
}
