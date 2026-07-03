#lang sicp



(define x '((a b) c d))
(define y '(e f))

(set-car! x y)

(set-car! y 'h)
x
y
