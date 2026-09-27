---
name: zenbpm-bpmn
description: Author, edit, and validate BPMN 2.0 and DMN files for ZenBPM. The files must also open in Camunda Modeler 8. Use this skill to create or change .bpmn and .dmn files in this repository. Use it also to wire the zenbpm or zeebe extensions: taskDefinition, ioMapping, taskHeaders, assignmentDefinition, calledDecision, calledElement, loopCharacteristics, and the message correlationKey. Use it also to confirm that a model parses in the ZenBPM model packages and has no unsupported element.
---

# Authoring ZenBPM BPMN & DMN models

Use this skill to create or change `.bpmn` and `.dmn` files in this repository.
Examples are files for examples, test fixtures, and documents. Make sure that
each model is valid for ZenBPM and for Camunda Modeler 8.

## Ground rules

1. Use the `zeebe:` namespace for the extensions.
   - The engine compares extension elements by XML local name. Therefore the
     prefixes `zeebe:` and `zenbpm:` both work.
   - Camunda Modeler 8 shows a `zeebe:` element as a Camunda 8 property. The
     Modeler does not show a `zenbpm:` element.
   - Use these elements: `zeebe:taskDefinition`, `zeebe:ioMapping`,
     `zeebe:taskHeaders`, `zeebe:assignmentDefinition`, `zeebe:calledDecision`,
     `zeebe:calledElement`, `zeebe:loopCharacteristics`, and
     `zeebe:subscription`.
   - Add `xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"` and
     `xmlns:modeler="http://camunda.org/schema/modeler/1.0"` to
     `<bpmn:definitions>`.
   - Add `modeler:executionPlatform="Camunda Cloud"` and
     `modeler:executionPlatformVersion="8.6.0"` to `<bpmn:definitions>`.

2. Always add the diagram interchange (DI).
   - Camunda Modeler does not make a layout.
   - Add a `bpmndi:BPMNShape` for each flow node.
   - Add a `bpmndi:BPMNEdge` with waypoints for each sequence flow.
   - Put the XML of the children of an expanded sub-process in the
     `<bpmn:subProcess>` element.
   - Put the DI shape of each child flat on the plane. Use absolute
     coordinates.
   - Put a boundary event in the center of the border of the host element. Use
     the attribute `attachedToRef`.

3. Propagate variables only with `zeebe:ioMapping`.
   - Activity variables go only through the mapping.
   - **Business rule task:** the result of the decision is a local variable. Add
     an output mapping. Example: `=feasibility → feasibility`. Without the
     mapping, a downstream condition does not see the variable. A decision table
     with the output name `feasible` gives the object `{ "feasible": ... }`.
     Therefore the expression `=feasibility.feasible = true` works.
   - **Call activity:** the input mappings fill the called instance. The parent
     process gets only the variables in the output mappings. The engine
     evaluates an output mapping against the variables of the called instance.
   - **Service task and user task:** the output mappings can read the result
     variables of the job. The process cannot read the result variables without
     a mapping.
   - The input mappings must supply the variables that the DMN or a downstream
     expression uses.

4. Put a condition only on a flow that leaves an Exclusive Gateway or an
   Inclusive Gateway.
   - The engine ignores a `conditionExpression` on a different flow.
   - Use the attribute `default="Flow_X"` on the gateway for the fallback
     branch.

5. Use only the supported elements. See `reference/supported-elements.md`.
   - The engine does not support these elements: Script Task, Manual Task,
     Complex Gateway, Signal events, Conditional events, Escalation events,
     Compensation events, message flow, data association, conditional flow,
     loop marker, ad-hoc marker, and compensation marker.
   - The engine puts an unsupported child element in `TProcess.UnknownElements`.
     Keep this list empty.

6. Make the diagram clear.
   - Use one main horizontal band.
   - Put the side branches below the main band.
   - Make each sub-process box large enough for its children.
   - Give each node a `name`.

7. Write all output that is not code in ASD-STE100 (Simplified Technical
   English).
   - This rule applies to prose: chat answers, `<bpmn:documentation>`,
     documents, commit messages, and comments.
   - Code, XML, identifiers, and commands are not prose. Do not change them.
   - Write one instruction in each sentence. Give an instruction a maximum of
     20 words. Give a description a maximum of 25 words.
   - Use the imperative mood for an instruction.
   - Use the active voice.
   - Use the simple present, the simple past, or the simple future tense. Do not
     use the continuous tense or the perfect tense.
   - Use one term for one concept. Do not use a synonym for the same concept.
   - Use the usual word. Do not use slang, idioms, or jargon.
   - Do not make a long noun cluster. Write "the state of the job". Do not write
     "the job state check".
   - Write a procedure as a vertical list. Put one step in each list item.
   - Keep the articles. Keep the subject and the verb. Do not remove words to
     make the text shorter.

8. Do not change a Markdown (`.md`) file until the user gives an explicit
   command.
   - This rule includes this skill and all other `.md` files.
   - You can read a `.md` file at any time.
   - Wait for an explicit command before you write to a `.md` file.

## Extension cheat-sheet

Use one of these elements for the job type of a service task, a send task, or a
user task:
```xml
<zeebe:taskDefinition type="my-job-type" />
```
Add static task headers:
```xml
<zeebe:taskHeaders><zeebe:header key="k" value="v" /></zeebe:taskHeaders>
```
Map variables with FEEL. Use the prefix `=`:
```xml
<zeebe:ioMapping>
  <zeebe:input source="=order.totalAmount" target="orderAmount" />
  <zeebe:output source="=decision.result" target="decisionResult" />
</zeebe:ioMapping>
```
Send a user task to a user or a group:
```xml
<zeebe:assignmentDefinition assignee="=planner.id" candidateGroups="production-planners" />
```
Call a decision from a business rule task:
```xml
<zeebe:calledDecision decisionId="production_feasibility" resultVariable="feasibility" />
```
Call a process from a call activity:
```xml
<zeebe:calledElement processId="procurement" />
```
Add the multi-instance marker to a task, a sub-process, or a call activity:
```xml
<bpmn:multiInstanceLoopCharacteristics isSequential="false">
  <bpmn:extensionElements>
    <zeebe:loopCharacteristics inputCollection="=bom.components" inputElement="component"
        outputCollection="results" outputElement="={ ok: ok }" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```
Define a message with a correlation key. Use the message in a message catch
event or in the start event of an event sub-process:
```xml
<bpmn:message id="Message_X" name="shipment-confirmed">
  <bpmn:extensionElements><zeebe:subscription correlationKey="=order.id" /></bpmn:extensionElements>
</bpmn:message>
```
A receive task refers to the message with the attribute:
`<bpmn:receiveTask ... messageRef="Message_X">`.

Define an error with `<bpmn:error id="Error_X" name="..." errorCode="MY_CODE" />`.
Throw the error with an error end event. Use `<bpmn:errorEventDefinition errorRef="Error_X" />`
in a scope. Catch the error with an error boundary event on the scope. The engine
matches the error code.

Add a timer:
```xml
<bpmn:timerEventDefinition>
  <bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT24H</bpmn:timeDuration>
</bpmn:timerEventDefinition>
```
The engine also supports `timeDate` and `timeCycle`. `timeCycle` uses the
ISO-8601 repeat syntax.

## Runtime semantics that shape the model

- A user task is a job. The default type is `user-task-type`. Set
  `zeebe:taskDefinition` to change the type. The engine has no tasklist product.
  Build the tasklist in your application with the job API. Use `getJobs` with a
  filter for `assignee`, `type`, or `state`. Then use `/jobs/{key}/assign`,
  `/complete`, `/fail`, and `/extend-lock`. Store a `formKey` as a mapped
  variable.
- The state of a job is durable. The engine stores the state in rqlite. The lock
  of a job is a lease in the memory of the partition leader. Therefore the
  engine can deliver a job more than one time. Make each handler idempotent.
- The engine reads the attribute `retries` from `taskDefinition`, but the engine
  does not use it. A failed job makes an incident.
- The engine completes or fails a job by the job key. The lock holder is not
  important.
- For a long task (hours or days), do not hold a job. Use a Receive Task or a
  message catch event. The external system completes the wait with a message.
  The correlation key only sends the message to the correct instance. The result
  goes in the payload variables.

## Validation workflow

Run these steps before you finish.

1. Check the XML. Run `xmllint --noout <file>`.
2. Check the references, the DI, and the element support. Run this command:
   ```
   python3 .agents/skills/zenbpm-bpmn/scripts/validate.py examples/*.bpmn
   ```
3. Check the parser. The program must stay in the module. The program imports
   the model packages. Run these commands from the module root:
   ```
   mkdir -p .tmp-parsecheck
   cp .agents/skills/zenbpm-bpmn/scripts/parsecheck.go .tmp-parsecheck/main.go
   go run ./.tmp-parsecheck examples/foo.bpmn examples/bar.dmn
   rm -rf .tmp-parsecheck
   ```
   For BPMN, the value `unknown=0` is correct. For DMN, the output shows the
   decision id, the inputs, and the outputs. Delete the folder `.tmp-parsecheck`
   after the check.

## Conventions for examples

- Put a model in the folder `examples/`.
- Use the element documents in `docs/reference/bpmn/supported-elements/` and the
  files in `pkg/bpmn/test-cases/` as a reference.
- Describe the purpose of the process with `<bpmn:documentation>`.
- Do not write a large DI by hand. A large DI causes errors. Write a temporary
  script. Run the validation steps. Then delete the script.
- Do not commit a generator, a scratch folder, or an AppleDouble file (a file
  with the prefix `._`).
