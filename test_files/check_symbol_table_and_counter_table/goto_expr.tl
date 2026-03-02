:x = 10
:y = 20
:dx = 5
:dy = 3
penup
goto (:x + :dx, :y * 2)
pendown
forward :dx
goto (:x - :dy, :y + :dx)
forward :dy
