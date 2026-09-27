#!/usr/bin/env python3
"""Validate ZenBPM BPMN files.

The program checks five items:
1. The file is well-formed XML.
2. The root element is bpmn:definitions.
3. All references resolve.
4. Each flow node has a shape. Each sequence flow has an edge.
5. The file has no unsupported element or construct.

Usage:
    python3 validate.py file1.bpmn [file2.bpmn ...]

The program prints one line for each file. The exit code is not zero if a file
has a problem.
"""
import sys
import xml.etree.ElementTree as ET

BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"

NODE_TAGS = {
    "startEvent", "endEvent",
    "serviceTask", "userTask", "businessRuleTask", "sendTask", "receiveTask",
    "callActivity", "subProcess",
    "exclusiveGateway", "inclusiveGateway", "parallelGateway", "eventBasedGateway",
    "intermediateCatchEvent", "intermediateThrowEvent",
    "boundaryEvent",
}
CONTAINER_ALLOWED = NODE_TAGS | {"sequenceFlow"}
# A container may also hold these members.
CONTAINER_EXTRA = {
    "documentation", "extensionElements", "incoming", "outgoing",
    "laneSet", "ioSpecification", "dataObject", "dataObjectReference",
    "property", "association", "textAnnotation", "multiInstanceLoopCharacteristics",
}
# Event definitions ZenBPM supports.
SUPPORTED_DEFS = {"messageEventDefinition", "timerEventDefinition",
                  "linkEventDefinition", "errorEventDefinition"}
# Definitions that make an intermediate throw event supported.
THROW_DEFS = {"messageEventDefinition", "linkEventDefinition"}
# The engine evaluates a condition only on a flow that leaves one of these.
CONDITION_GATEWAYS = {"exclusiveGateway", "inclusiveGateway"}


def local(tag):
    return tag[len(BPMN):] if tag.startswith(BPMN) else None


def check(path):
    problems = []
    root = ET.parse(path).getroot()
    if root.tag != BPMN + "definitions":
        print(f"{path}: the root element is not bpmn:definitions")
        return False

    tag_of = {e.get("id"): local(e.tag) for e in root.iter() if e.get("id")}
    node_ids = {i for i, t in tag_of.items() if t in NODE_TAGS}
    message_ids = {i for i, t in tag_of.items() if t == "message"}
    error_ids = {i for i, t in tag_of.items() if t == "error"}
    flow_ids = {i for i, t in tag_of.items() if t == "sequenceFlow"}

    # Check the references.
    for e in root.iter(BPMN + "sequenceFlow"):
        for role in ("sourceRef", "targetRef"):
            if e.get(role) not in node_ids:
                problems.append(f"flow {e.get('id')}: {role} {e.get(role)} is not a flow node")
    for e in root.iter(BPMN + "boundaryEvent"):
        if e.get("attachedToRef") not in node_ids:
            problems.append(f"boundary {e.get('id')}: attachedToRef {e.get('attachedToRef')} is not a flow node")
    for tag in ("exclusiveGateway", "inclusiveGateway"):
        for e in root.iter(BPMN + tag):
            if e.get("default") and e.get("default") not in flow_ids:
                problems.append(f"gateway {e.get('id')}: default {e.get('default')} is not a flow")
    for e in root.iter(BPMN + "receiveTask"):
        if e.get("messageRef") not in message_ids:
            problems.append(f"receiveTask {e.get('id')}: messageRef {e.get('messageRef')} is not a message")
    for e in root.iter(BPMN + "messageEventDefinition"):
        if e.get("messageRef") and e.get("messageRef") not in message_ids:
            problems.append(f"messageEventDefinition {e.get('id')}: messageRef {e.get('messageRef')} is not a message")
    for e in root.iter(BPMN + "errorEventDefinition"):
        if e.get("errorRef") and e.get("errorRef") not in error_ids:
            problems.append(f"errorEventDefinition {e.get('id')}: errorRef {e.get('errorRef')} is not an error")

    # Check the conditions. A condition is valid only after a matching gateway.
    for e in root.iter(BPMN + "sequenceFlow"):
        if e.find(BPMN + "conditionExpression") is None:
            continue
        if tag_of.get(e.get("sourceRef")) not in CONDITION_GATEWAYS:
            problems.append(f"flow {e.get('id')}: a condition is allowed only after an exclusive or an inclusive gateway")

    # Find unsupported elements and constructs.
    containers = list(root.iter(BPMN + "process")) + list(root.iter(BPMN + "subProcess"))
    for container in containers:
        for child in container:
            lt = local(child.tag)
            if lt is None or lt in CONTAINER_ALLOWED or lt in CONTAINER_EXTRA:
                continue
            problems.append(f"unsupported element <bpmn:{lt}> in {container.get('id')}")
    for e in root.iter(BPMN + "standardLoopCharacteristics"):
        problems.append("unsupported loop marker on a task (standardLoopCharacteristics)")
    for e in root.iter(BPMN + "intermediateThrowEvent"):
        defs = {local(c.tag) for c in e}
        if not (defs & THROW_DEFS):
            problems.append(f"intermediateThrowEvent {e.get('id')}: a none intermediate throw event is not supported")
    for e in root.iter():
        lt = local(e.tag)
        if lt and lt.endswith("EventDefinition") and lt not in SUPPORTED_DEFS:
            problems.append(f"unsupported event definition <bpmn:{lt}> on {e.get('id')}")

    # Check the diagram interchange (DI) coverage.
    shapes = {s.get("bpmnElement") for s in root.iter(DI + "BPMNShape")}
    edges = {s.get("bpmnElement") for s in root.iter(DI + "BPMNEdge")}
    for i in node_ids:
        if i not in shapes:
            problems.append(f"no BPMNShape for {i}")
    for i in flow_ids:
        if i not in edges:
            problems.append(f"no BPMNEdge for {i}")

    status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
    print(f"{path}: nodes={len(node_ids)} flows={len(flow_ids)} shapes={len(shapes)} edges={len(edges)} -> {status}")
    for p in problems:
        print(f"  - {p}")
    return not problems


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    ok = True
    for path in argv[1:]:
        try:
            ok = check(path) and ok
        except ET.ParseError as err:
            print(f"{path}: XML parse error: {err}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
