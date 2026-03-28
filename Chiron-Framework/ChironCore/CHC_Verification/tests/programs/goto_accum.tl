:x = 20
:y = 0
goto (:x, :y)
repeat 3 [
  :x = :x + 10
  :y = :y + 5
  goto (:x, :y)
]
