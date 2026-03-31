:a = :start
:b = :start
:c = :start
:d = :start
repeat 4 [
  :a = :a + 1
  repeat 4 [
    :b = :b + 1
    repeat 4 [
      :c = :c + 1
      repeat 4 [
        :d = :d + 1
      ]
    ]
  ]
]
