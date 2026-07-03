#lang sicp

(define (make-decrementer balance)
  (lambda (amount)
    (- balance amount)))
(define D1 (make-decrementer 25))
(define D2 (make-decrementer 25))
(eq? D1 D2) ; => #f
(eqv? D1 D2) ; => #f
(equal? D1 D2) ; => #f

(define D3 D2)
(eq? D2 D3)
(eqv? D2 D3)
(equal? D2 D3)
