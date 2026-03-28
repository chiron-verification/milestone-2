:val = :a
if (:val > 0) [
  if (:val > 100) [
    :val = 100
  ] else [
    :val = :val * 2
  ]
] else [
  :val = 0
]
