import { answerScenarios, type AnswerScenario } from "./answers";

export interface Conversation {
  id: string;
  title: string;
  startedAt: string;
  scenarioIds: string[];
}

export const conversations: Conversation[] = [
  {
    id: "convo-termination",
    title: "Can my employer fire me without notice?",
    startedAt: "2026-09-27 10:14 AM",
    scenarioIds: ["labor-termination", "decline-pension"],
  },
  {
    id: "convo-warranty",
    title: "The store won't honor my warranty. What are my rights?",
    startedAt: "2026-09-24 3:41 PM",
    scenarioIds: ["consumer-warranty"],
  },
  {
    id: "convo-mixed",
    title:
      "I was fired without due process and now my landlord won't return my security deposit.",
    startedAt: "2026-09-20 9:02 AM",
    scenarioIds: ["mixed-termination-deposit", "out-of-scope-malpractice"],
  },
];

export function getConversationTurns(conversation: Conversation): AnswerScenario[] {
  return conversation.scenarioIds
    .map((id) => answerScenarios.find((s) => s.id === id))
    .filter((s): s is AnswerScenario => Boolean(s));
}
