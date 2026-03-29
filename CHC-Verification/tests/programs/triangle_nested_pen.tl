:side = 20
:step = 0
repeat 2 [
  pendown
  repeat 3 [
    forward :side
    right 120
    :step = :step + 1
  ]
  penup
  left 60
  forward 15
  right 60
  :side = :side + 10
]
