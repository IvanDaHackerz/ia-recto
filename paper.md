Technological Institute of the Philippines
Quezon City

College of Computer Studies
Computer Science Department

CS 403 – Intelligent Agents
First Semester S.Y. 2026-2027

CONCEPT PROPOSAL

Recto & Co. Legal: A Web-Based Intelligent Agent for Accessible Philippine Labor and Consumer Rights Information 



(3) Background of the Study (Brief description of the target beneficiary. The proponents will present the problems encountered by the end users in the procedure of the existing system.)

Access to legal information remains a persistent problem for ordinary Filipino workers and consumers. In the World Justice Project's 2025 Rule of Law Index, the Philippines ranked 97th out of 143 countries (World Justice Project, 2025). Civil justice was among the areas that weakened worldwide, and the country's overall score has barely moved since 2023 (Rappler, 2023; BusinessWorld Online, 2024).
Part of the problem is a shortage of lawyers relative to demand. As of November 2022, the Philippines had 84,236 lawyers listed in the Supreme Court's Roll of Attorneys against a population of over 117 million (Tribune, 2023). The Public Attorney's Office (PAO), which provides free legal help to those who can't afford a lawyer, handled over 850,000 cases in 2022 alone, with each lawyer managing around 5,300 cases a year (Philippine News Agency, 2024; Philippine Information Agency, 2023), a workload that limits how much attention each client can realistically get.
This gap is especially visible in labor and consumer issues, which generate substantial demand for government dispute resolution and consumer-complaint services. DOLE resolved labor disputes affecting over 109,000 workers in 2025 (Philippine News Agency, 2026), while DTI received nearly 29,000 consumer complaints in 2023 (Philstar.com, 2024). Notably, in one reporting period, only about 30% of complaints DTI received actually fell under its jurisdiction, with the rest needing referral elsewhere (Inquirer Business, 2023), showing that many people don't even know where to seek help. The system also addresses the accessibility needs of persons with disabilities through features such as adjustable text sizing and high-contrast presentation.
Existing options also present limitations. Private legal services may be inaccessible for people seeking answers to routine questions, while government legal-aid services may have limited capacity. Generic AI chatbots and search engines may also provide answers that are not sufficiently specific to Philippine law, lack identifiable legal sources, or present information without making it easy for users to verify the basis of the response. These limitations are particularly important in legal-information systems, where unsupported or outdated claims can have serious consequences. Rather than attempting to cover all areas of Philippine law, this study proposes a narrower and more controllable scope focused on labor and consumer rights. Within this scope, the system is designed to provide source-grounded information, display the legal material used to support its responses, identify questions or portions of questions outside its supported domains, and avoid generating substantive claims when sufficient supporting evidence cannot be retrieved.
This study is aligned with UN Sustainable Development Goal 16 (Peace, Justice and Strong Institutions), particularly the goal of ensuring equal access to justice for all, and supports SDG 8 (Decent Work and Economic Growth) and SDG 10 (Reduced Inequalities) by helping workers and consumers understand their rights.
(4) Project Objectives (What do you want to accomplish in your investigation? The proponents will present the solutions that will answer all the problems in the existing system.)

General Objective:
To develop and evaluate a web-based intelligent agent that provides accessible, source-grounded information on Philippine labor and consumer rights, while identifying out-of-scope and mixed-domain questions and avoiding unsupported legal claims.
Specific Objectives:
To build a focused and well-organized legal knowledge base and classification system covering selected Philippine labor and consumer protection topics, using Presidential Decree No. 442 (The Labor Code of the Philippines, as amended), Republic Act No. 7394 (The Consumer Act of the Philippines), and relevant post-1987 Republic Acts from the BetterGov.PH Philippine Legal Documents Library. The classification component will identify the supported legal domain or domains, including mixed-domain questions, and flag questions containing unsupported legal domains. Its performance will be evaluated using accuracy, precision, recall, F1-score, and confusion-matrix analysis.
To design a retrieval and citation-verification system that identifies relevant sections of the supported legal sources for a user's question, provides answers only when sufficient supporting evidence is retrieved, and verifies that cited provisions correspond to the legal text used to generate the response, thereby reducing unsupported or fabricated citations and legal claims.
To design the system as a goal-based intelligent agent that checks the user's input, identifies the legal topic, finds relevant legal sources, checks for known amendments or repeals, verifies citations, checks the reliability of the retrieved information, and handles questions that are outside the system's scope. The system will also show the date when the legal sources were last checked. If a question contains both supported and unsupported legal topics, the agent will answer only the supported part and clearly identify the part that is outside its scope.
To develop an accessible and user-friendly web application with saved chat history, a Q&A interface displaying the legal sources retrieved for each response, and accessibility features such as adjustable text sizing and high-contrast presentation. The system will store relevant interaction and evaluation data for analysis, and selected system responses will be reviewed by a licensed legal professional to assess the legal relevance, source support, and clarity of the generated information.
(5) Expected Output (Indicate the specific products, processes, or services which the project is expected to produce. The final project must be reliable, efficient, user-friendly, and accessible to all users, especially for PWD personnel.)
The project will produce a complete, working web-based prototype, made up of:
A focused legal knowledge base - cleaned and filtered primary sources including Presidential Decree No. 442 (The Labor Code of the Philippines, as amended), Republic Act No. 7394 (The Consumer Act of the Philippines), and related post-1987 Republic Acts relevant to Philippine labor and consumer protection, including section-level text, source metadata, effectivity information, and recorded relationships to subsequent amendments or repeals where such information is available from designated legal sources. Each source record will include a verification or knowledge-base update date so that the system can show when its legislative-status information was last checked.
A trained legal-topic classifier - identifies whether a question concerns labor law, consumer protection, both supported domains, or one or more unsupported domains. The classifier will support mixed-domain detection and will be evaluated using accuracy, precision, recall, F1-score, and confusion-matrix analysis. It is trained on a labeled dataset of user-style questions, annotated as labor, consumer, mixed, or out-of-scope.
A retrieval and citation-verification system - retrieves relevant legal sections from the supported knowledge base, uses a defined confidence or evidence threshold before generating substantive responses, and checks whether citations in the generated response correspond to the retrieved legal text.
An intelligent agent layer - coordinates input checking, legal-topic classification, source retrieval, amendment and repeal checking, citation verification, confidence checking, and response generation. The system will show when the legal information was last checked and will identify any known amendments or repeals found in the sources. If a question contains both supported and unsupported legal topics, the system will answer only the supported part and clearly explain which part is outside its scope. For questions that are completely outside the system's scope, it will provide a notice and, when appropriate, direct users to relevant government offices or legal-assistance services.
A web-based interface with saved chat history - a simple question-and-answer page with plain-language explanations by default, with the option to view the exact legal text and citation for users who want more detail, alongside a side panel showing the real law text. Includes a saved history feature so users can revisit their past questions and answers, adjustable text sizing, and a high-contrast display option for PWD users. 
A database - stores user queries, classification results, sources used, citation-verification results, and chat history for session recall.
A written report - explaining how the system was built, how the data was chosen and cleaned, how well the classifier and retrieval performed, and how a lawyer reviewed the system's answers.
The final system will aim to provide understandable, source-grounded responses within its defined labor and consumer scope, while clearly communicating uncertainty and scope limitations. Its performance, usability, accessibility, and source-grounding behavior will be evaluated using defined technical metrics and user or expert assessment.
(6) Significance of the Study (Contributions of the project/study.  This section justifies the study. It should include a statement of the contribution of the study in pushing back the existing frontiers of knowledge. It should also include the potential beneficiaries of the research and the possible uses of the results.)
This study puts intelligent agent concepts like goal-based reasoning and knowledge representation to use in a real, socially meaningful problem, where getting things right (and being honest about what it doesn't know) actually matters to the person using it. This goes beyond the usual classroom examples of agents and applies the same ideas to something with real consequences.
The study responds to a real and ongoing problem in the Philippines: civil justice access has stayed weak for years (World Justice Project, 2025), and there is substantial demand for legal assistance, as shown by the rising number of cases handled by the Public Attorney's Office (Philippine News Agency, 2024). By focusing specifically on labor and consumer law, the study concentrates its resources on two areas with documented demand for government assistance and complaint resolution, as reflected in reported labor-dispute and consumer-complaint figures. The narrower scope also allows the proponents to conduct more controlled testing of classification, retrieval, citation verification, and scope detection rather than attempting shallow coverage of the entire Philippine legal system.
The study focuses on a clear and limited scope and gives importance to checking the sources used by the system. Instead of trying to cover many areas of law, the proposed system focuses on whether its answers about labor and consumer law are supported by actual legal sources, whether its citations match the sources used, and whether it can recognize questions that are outside its scope. This gives the study a clear way to test how reliably a narrowly focused legal-information system can retrieve and present source-supported information within its defined scope.
Who this could help:
Ordinary Filipino workers and consumers, who can access free, accessible, source-grounded information about labor and consumer rights within the system's defined scope.
Legal aid groups, government agencies, and other organizations may use the system as a supplementary source of publicly accessible legal information, while the study does not assume that it will replace professional legal assistance or reduce agency workload.
Persons with Disabilities (PWDs), who make up a significant share of the population according to national census data (Philippine Statistics Authority, 2022), and who benefit directly from the system's accessible design.
Students and researchers, who could build on this study's approach, which is the citation-checking system and the way the knowledge base was scoped, for future work on intelligent agents or legal technology.
The system's design could later be used as a starting point for building similar tools for other legal topics (like tenant rights or family law), or even for completely different public-information problems, using the same core ideas developed here.
(7) Target Beneficiaries (Who the clientele are and what are the expected outcomes/effects of the use of the project output?)
This system is primarily intended for ordinary Filipino citizens who need quick, understandable, and source-grounded information about everyday labor and consumer concerns. It is designed for the general public rather than legal professionals.
Primary beneficiaries:
Filipino workers with labor concerns (wage disputes, illegal dismissal, overtime pay, contract terms).
Filipino consumers with consumer concerns (defective products, warranty claims, deceptive sales, service disputes).
Persons with Disabilities (PWD), who benefit from the system's accessible design.
Expected outcomes:
Better understanding of labor and consumer rights based on the legal sources supported by the system.
Greater access to source-grounded legal information that users can check against the cited legal material.
A clearer understanding of when a question falls within the system's supported legal scope and when seeking assistance from a qualified legal professional or appropriate government office may be necessary.
Ability to receive information about the labor or consumer aspects of a mixed-domain question while being informed when another aspect falls outside the system's supported scope.
Ability to revisit past questions through saved chat history.
A scope and limitation notice - informs users that the system provides general legal information within its supported labor and consumer domains, does not replace professional legal advice, and may identify questions that require assistance outside its supported scope
(8) Remarks (To Be Filled out by the Faculty In-Charge)







Noted by: 							

_______________________ 				
Mr. Jess N. Garcia              					
Faculty In-Charge 													
References:

BusinessWorld Online. (2024, October 23). PHL rule of law improves but still among worst in region. https://www.bworldonline.com/the-nation/2024/10/23/630311/phl-rule-of-law-improves-but-still-among-worst-in-region/
Inquirer Business. (2023). Consumer complaints rose 4% from Jan to Aug, DTI says. Philippine Daily Inquirer. https://business.inquirer.net/425041/consumer-complaints-rose-4-from-jan-to-aug-dti-says
Philippine Information Agency. (2023, January 17). Villanueva pushes for scholarships for aspiring lawyers. https://mirror.pia.gov.ph/press-releases/2023/01/17/villanueva-pushes-for-scholarships-for-aspiring-lawyers
Philippine News Agency. (2024). 178 new PAO lawyers to help deliver justice for indigents. https://www.pna.gov.ph/articles/1229449
Philippine News Agency. (2026). DOLE posts 98.07% labor case disposition rate in 2025. https://www.pna.gov.ph/articles/1266059
Philippine Statistics Authority. (2022). Functional difficulty in the Philippines: For household population five years old and over (2020 Census of Population and Housing). https://psa.gov.ph/statistics/population-and-housing/node/168274
Philstar.com. (2024, March 19). Consumer complaints rise in 2023 – DTI. https://www.philstar.com/business/2024/03/19/2341515/consumer-complaints-rise-2023-dti
Rappler. (2023). Rule of law in Philippines still among the worst in East Asia. https://www.rappler.com/philippines/ranking-rule-law-index-world-justice-project-2023/
Tribune. (2023, September 17). Setting the bar high. https://tribune.net.ph/2023/09/17/setting-the-bar-high
World Justice Project. (2025). WJP Rule of Law Index: Philippines insights. https://worldjusticeproject.org/rule-of-law-index/country/Philippines


## Implementation and evaluation status — 19 October 2026

This dated implementation note distinguishes the working local prototype from the proposal's required final acceptance. The custom classifier, filtered retrieval, source/citation verifier and local React website are connected. The current bindings are classifier v1.5.15, retrieval v1.3.1 and verifier v1.0.9. Optional conditional wording interpretation and recorded-source explanations use Together.ai; generation selects exact source passages and a separate same-model automated support check must pass. Those checks do not establish independent legal correctness or source currentness.

Opt-in Windows-user encrypted, browser-scoped local history now stores question/classification/source/verification-response packets, with opening, export, deletion and 30-day retention. Reading controls, source inspection, measured development metrics, local-only AI choice, request cancellation and local operating limits are implemented. This remains a loopback development system, not a deployed public legal service.

The latest local-only frozen replay reuses 436 AI development inputs across 171 related wording families: topic/coverage match 425/425 labeled forms, routes 435/436, and known-relevant retrieval Hit@5 93/93 judged groups. The complete application replay returns 436/436 packets, topic/coverage 424/425 and routes 435/436; 82 explanations containing 125 paragraphs pass exact citations and same-model automated support, while 354 are withheld for recorded reasons. These are inspected synthetic development results. They are not independent-human accuracy, population confidence, legal-answer F1 or licensed-professional review. The same cases and labels were preserved across software repair replays; all runs and failures remain recorded.

The current software record includes 162 backend tests, 65 classifier tests, 43 retrieval tests, 37 verifier tests, 16 additional concern/intake/referral tests and 16 frontend interaction/structural accessibility tests. Build/lint, metric reconciliation, dependency scans and a fresh Python dependency/runtime check pass. Tests and automated review do not replace legal or user assessment. See outputs/project-repair-v1.0.0/REPORT.md for exact provenance, limits, logs and the original 32-gap disposition.

Fresh independent-human intake still contains zero authored questions. Source/currentness and claim reviews, the pending extraction queue, actual legal-professional review, assistive-technology/user assessment and owner/team/adviser acceptance remain unfinished. The 125 generated paragraphs have a review queue with blank independent verdicts; no human approval is inferred or fabricated. Public deployment and the previously pasted provider key's rotation remain separate owner operations.
