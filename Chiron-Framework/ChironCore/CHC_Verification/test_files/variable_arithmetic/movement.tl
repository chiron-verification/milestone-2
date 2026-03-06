:step = 20
:count = 0
:total = 0
forward :step
:total = :total + :step
:count = :count + 1
:step = :step + 15
forward :step
:total = :total + :step
:count = :count + 1
:step = :step * 2
forward :step
:total = :total + :step
:count = :count + 1
:avg = :total / 3
