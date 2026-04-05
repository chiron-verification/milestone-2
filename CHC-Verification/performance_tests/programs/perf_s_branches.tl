:x = 0
:acc = 0
:t1 = :thresh
:t2 = :thresh + 1
:t3 = :thresh + 2
:t4 = :thresh + 3
repeat 8 [
  :x = :x + 1
  if (:x > :t1) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > :t2) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > :t3) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
  if (:x > :t4) [
    :acc = :acc + 1
  ] else [
    :acc = :acc + 0
  ]
]
