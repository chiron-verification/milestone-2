:arm = 10
:count = 0
repeat 3 [
  pendown
  repeat 2 [
    forward :arm
    left 30
    forward :arm
    right 60
    :count = :count + 1
  ]
  penup
  right 120
  :arm = :arm + 5
]
