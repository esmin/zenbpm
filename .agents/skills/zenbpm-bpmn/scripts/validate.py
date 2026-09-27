#!/usr/bin/env python3
"""Validate ZenBPM BPMN files.

The program checks four items:
1. The file is well-formed XML.
2. All references resolve.
3. Each flow node has a shape. Each sequence flow has an edge.
4. The file has no unsupported element.

Usage:
    python3 validate.py file1.bpmn [file2.bpmn ...]

The program prints one line for each file. The exit code is not zero if a file
has a problem.
"""
import sys
import xml.etree.ElementTree as ET

BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"

SUPPORTED_NODES = {
    "startEvent", "endEvent",
    "serviceTask", "userTask", "businessRuleTask", "sendTask", "receiveTask",
    "callActivity", "subProcess",
    "exclusiveGateway", "inclusiveGateway", "parallelGateway", "eventBasedGateway",
    "intermediateCatchEvent", "intermediateThrowEvent",
    "boundaryEvent",
}
# BPMN structural children allowed inside a flow-element container.
CONTAINER_ALLOWED = SUPPORTED_NODES | {"sequenceFlow"}
# Event definitions ZenBPM actually supports.
SUPPORTED_DEFS = {"messageEventDefinition", "timerEventDefinition",
                  "linkEventDefinition", "errorEventDefinition"}


def check(path):
    problems = []
    root = ET.parse(path).getroot()

    ids = {e.get("id") for e in root.iter() if e.tag.startswith(BPMN) and e.get("id")}
    nodes = [(e.get("id"), t) for t in SUPPORTED_NODES for e in root.iter(BPMN + t)]
    flows = [(e.get("id"), e.get("sourceRef"), e.get("targetRef"))
             for e in root.iter(BPMN + "sequenceFlow")]

    # Check the references
    for fid, s, d in flows:
        if s not in ids:
            problems.append(f"flow {fid}: missing source {s}")
        if d not in ids:
            problems.append(f"flow {fid}: missing target {d}")
    for e in root.iter(BPMN + "boundaryEvent"):
        if e.get("attachedToRef") not in ids:
            problems.append(f"boundary {e.get('id')}: missing attachedToRef {e.get('attachedToRef')}")
    for tag in ("exclusiveGateway", "inclusiveGateway"):
        for e in root.iter(BPMN + tag):
            if e.get("default") and e.get("default") not in ids:
                problems.append(f"gateway {e.get('id')}: missing default {e.get('default')}")
    for e in root.iter(BPMN + "receiveTask"):
        if e.get("messageRef") not in ids:
            problems.append(f"receiveTask {e.get('id')}: missing messageRef {e.get('messageRef')}")
    for e in root.iter(BPMN + "messageEventDefinition"):
        mr = e.get("messageRef")
        if mr and mr not in ids:
            problems.append(f"messageEventDefinition {e.get('id')}: missing messageRef {mr}")
    for e in root.iter(BPMN + "errorEventDefinition"):
        er = e.get("errorRef")
        if er and er not in ids:
            problems.append(f"errorEventDefinition {e.get('id')}: missing errorRef {er}")

    # Find unsupported elements and unsupported event definitions
    for container in list(root.iter(BPMN + "process")) + list(root.iter(BPMN + "subProcess")):
        for child in container:
            if not child.tag.startswith(BPMN):
                continue
            local = child.tag[len(BPMN):]
            if local not in CONTAINER_ALLOWED and local not in (
                "documentation", "extensionElements", "incoming", "outgoing",
                "multiInstanceLoopCharacteristics", "laneSet", "ioSpecification",
                "dataObject", "dataObjectReference", "property", "association", "textAnnotation",
            ):
                problems.append(f"unsupported element <bpmn:{local}> in {container.get('id')}")
            if local == "multiInstanceLoopCharacteristics":
                if child.get("behavior") == "ComplexBehavior":
                    problems.append(f"complex loop marker on {container.get('id')}")
    for e in root.iter():
        if not e.tag.startswith(BPMN):
            continue
        local = e.tag[len(BPMN):]
        if local.endswith("EventDefinition") and local not in SUPPORTED_DEFS:
            problems.append(f"unsupported event definition <bpmn:{local}> on {e.get('id')}")

    # Check the diagram interchange (DI) coverage
    shapes = {s.get("bpmnElement") for s in root.iter(DI + "BPMNShape")}
    edges = {s.get("bpmnElement") for s in root.iter(DI + "BPMNEdge")}
    for i, t in nodes:
        if i not in shapes:
            problems.append(f"no BPMNShape for {t} {i}")
    for fid, _, _ in flows:
        if fid not in edges:
            problems.append(f"no BPMNEdge for {fid}")

    status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
    print(f"{path}: nodes={len(nodes)} flows={len(flows)} shapes={len(shapes)} edges={len(edges)} -> {status}")
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
