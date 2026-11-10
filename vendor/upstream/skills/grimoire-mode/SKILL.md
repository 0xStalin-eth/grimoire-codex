---
name: grimoire-mode
description: >-
    A grimoire guided approach for security research, in-depth reasoning and research, report and proofof concept development. Use while doing security research or invoked as /grimoire-mode. 
user_invocable: true
---

# grimoire

*Essential:*

* Never run anything against a production environment unless explicitly asked to do so! 
* Be consise and always use simple technical english.
* Always make sure you have read GRIMOIRE.md 
* Never produce a claim that relies on unverified assumptions. 
* Don't force findings where there are none.

## Tenets

Read the full skill for each principle you apply.

Core 
* finding - what does a good report look like
* tome    - an llm wiki inspired approach to incremental security research

## Agents 

* familiar - A helpful agent to ensure quality of findings, co-operative and assistive.
* hag - A strict but fair agent that adversarially reviews findings. A finding is only good enough once it's approved by the hag.
* gnome - A worker agent for building out scaffolding that supports security research.
* librarian - An agent that has extensive knowledge and capability for finding documentation and artifacts.
* scribe - An agent for documenting.
* sigil - An agent that performs autonomous research.

## Somatics ( workflows )

Workflows are skills that structure how you approach a goal.

* tome - Tomes are an incremental research wiki with extensive evidence provenance. Use it whenever a user asks a question, the tome skill provides a structured method for answering questions.
* delve - Surface odd behavior, near-misses, and leads from completed autonomous research to the operator. A report for humans, not a way for agents to pick their next task.
* dig-mode - Short question, short answer. Lets the operator build context on a system or on prior research with low cognitive load. Often follows delve.
* validate-hypothesis - Settle one hypothesis: explore, prove or disprove with a PoC, then promote it to a finding draft or close it as invalid or expected behavior.
