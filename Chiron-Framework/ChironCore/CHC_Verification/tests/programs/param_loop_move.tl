:x = :start
pendown
repeat 3 [
  :x = :x + :step
  goto (:x, 0)
]
penup
