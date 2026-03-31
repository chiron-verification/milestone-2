:a = :start
:b = :start
:c = :start
repeat 5 [
  :a = :a + 1
  repeat 5 [
    :b = :b + 1
    repeat 5 [
      :c = :c + 1
    ]
  ]
]
