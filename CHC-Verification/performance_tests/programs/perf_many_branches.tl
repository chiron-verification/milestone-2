:x = 0
:acc = 0
repeat 6 [
  :x = :x + 1
  if (:x > 1) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > 2) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > 3) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > 4) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
]
