:dx = 5
:dy = 2
:x = 0
:y = 0
repeat 4 [
  :x = :x + :dx
  :y = :y + :dy
  goto (:x, :y)
  right 15
  :dx = :dx + 5
  :dy = :dy + 3
]
