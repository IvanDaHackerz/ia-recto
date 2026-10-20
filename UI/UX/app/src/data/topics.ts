export interface Topic {
  id: string;
  label: string;
  description: string;
  domain: "labor" | "consumer";
  searchTerm: string;
}

export const topics: Topic[] = [
  {
    id: "wages",
    label: "Wages & pay",
    description: "Overtime, holiday pay, 13th-month pay, final pay.",
    domain: "labor",
    searchTerm: "pay",
  },
  {
    id: "termination",
    label: "Termination & due process",
    description: "Just cause, twin-notice rule, illegal dismissal.",
    domain: "labor",
    searchTerm: "termination",
  },
  {
    id: "warranties",
    label: "Warranties & refunds",
    description: "Repair, replacement, and refund rights.",
    domain: "consumer",
    searchTerm: "warranty",
  },
  {
    id: "sales-practices",
    label: "Deceptive sales & pricing",
    description: "Misleading ads, price tags, shortchanging.",
    domain: "consumer",
    searchTerm: "",
  },
];
