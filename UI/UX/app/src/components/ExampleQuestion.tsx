import { ArrowRight, Check } from "lucide-react";
import type { AnswerScenario } from "../data/answers";

const TOPICS = { labor: "Labor", consumer: "Consumer", mixed: "Mixed topics", out_of_scope: "Outside scope" };

export function ExampleQuestion({ example, selected, onPick }: {
  example: AnswerScenario;
  selected: boolean;
  onPick: (question: string) => void;
}) {
  return (
    <button className="example-question" type="button" data-selected={selected}
      aria-label={`Load example question: ${example.query}`} onClick={() => onPick(example.query)}>
      <span className="example-question-copy">
        <span className="example-question-text">{example.query}</span>
        <span className="example-topic">{selected ? "Added to your question field" : TOPICS[example.domain]}</span>
      </span>
      <span className="example-action" aria-hidden="true">
        {selected ? <Check size={20} strokeWidth={1.6} /> : <ArrowRight size={20} strokeWidth={1.6} />}
      </span>
    </button>
  );
}
