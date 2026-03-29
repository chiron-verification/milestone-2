:level = :threshold
:current = :value
penup
if (:current > :level) [
  pendown
  :current = :current - :level
] else [
  :current = :current + :level
]
