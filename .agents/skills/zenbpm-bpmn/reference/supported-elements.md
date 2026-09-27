# ZenBPM BPMN element support

Read `docs/reference/bpmn/supported-elements/`. That folder is the source of
truth. Read the folder again if a model parses in an unexpected way. The folder
and the engine stay in sync.

## Events

| Element | Supported |
|---|---|
| None Start Event | Yes |
| None End Event | Yes |
| Message Start Event | Yes |
| Message End Event | Yes |
| Message Intermediate Catch Event | Yes |
| Message Intermediate Throw Event | Yes |
| Message Boundary Event, interrupting | Yes |
| Message Boundary Event, non-interrupting | Yes |
| Timer Start Event | Yes |
| Timer Intermediate Catch Event | Yes |
| Timer Boundary Event, interrupting | Yes |
| Timer Boundary Event, non-interrupting | Yes |
| Link Intermediate Catch Event | Yes |
| Link Intermediate Throw Event | Yes |
| Error Boundary Event, interrupting | Yes |
| Error End Event | Yes |
| None Intermediate Throw Event | No |
| Escalation events | No |
| Conditional events | No |
| Signal events | No |
| Compensation events | No |

## Activities

| Element | Supported |
|---|---|
| Service Task | Yes |
| User Task | Yes |
| Business Rule Task | Yes |
| Send Task | Yes |
| Receive Task | Yes |
| Call Activity | Yes |
| Sub-Process, embedded | Yes |
| Event Sub-Process | Yes |
| Script Task | No |
| Manual Task | No |

A Receive Task can start a process instance. Set the attribute `instantiate` to
`true`.

## Activity markers

| Marker | Supported |
|---|---|
| Parallel multi-instance | Yes |
| Sequential multi-instance | Yes |
| Loop | No |
| Compensation | No |
| Ad-hoc | No |

## Gateways

| Gateway | Supported |
|---|---|
| Exclusive | Yes |
| Inclusive | Yes |
| Parallel | Yes |
| Event-Based | Yes |
| Complex | No |

## Flows

| Flow | Supported |
|---|---|
| Sequence flow | Yes |
| Default flow | Yes |
| Conditional flow | No |
| Message flow | No |
| Data association | No |

Notes:

- A conditional flow is a sequence flow that starts at an activity. The engine
  does not evaluate the condition on this flow. Route with an Exclusive Gateway
  or an Inclusive Gateway instead.
- The engine does not support a message flow. Use message events with a Send
  Task or a Receive Task.
- The engine does not support a data association. Pass data through variables.

## Notes

- The engine compares extension elements by XML local name. Therefore the
  prefixes `zeebe:` and `zenbpm:` both work. Use `zeebe:` to keep Camunda
  Modeler 8 compatible.
- The engine puts unsupported child elements in `TProcess.UnknownElements`. The
  parse check prints the count of these elements. The count must be 0.
