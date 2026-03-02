:a = 0
:b = 0
penup
goto (:a, :b)
pendown
:a = :a + 50
forward :a
penup
goto (:a, :b)
pendown
:b = :b + 50
right 90
forward :b
penup
goto (0, 0)
