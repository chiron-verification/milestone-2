:step = 0
:acc = 0
repeat 5 [
  :step = :step + 1
  if (:step > 2) [
    forward :step
    right 90
    :acc = :acc + :step
  ] else [
    left 90
    :acc = :acc + 1
  ]
]
