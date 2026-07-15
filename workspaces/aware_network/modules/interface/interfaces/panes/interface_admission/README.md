# Interface Admission Pane

`interface_admission` is the first canonical Aware Browser pane.

It is shown before Control, Identity, Actor, Environment, or workspace runtime
surfaces. A renderer enters or pairs into a durable `Interface`; an
`InterfaceSession` represents this renderer/device attachment.

This pane owns render intent only:

- view-state attributes are Interface Admission attributes, not inferred
  Identity or Control fields
- create/select/pair/resume action affordances are surfaced by Interface Host
  capability descriptors
- action execution remains disabled until the Interface Admission action pass
  commits the canonical Interface/InterfaceSession/InterfaceWindow truth

