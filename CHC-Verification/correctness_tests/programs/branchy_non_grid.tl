:step = 5
repeat 3 [
  if (:step > 6) [
    right 30
  ] else [
    right 10
  ]
  :step = :step + 2
]
