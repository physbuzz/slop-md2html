#lang sicp

(define zero (lambda (f) (lambda (x) x)))
(define (add-1 n)
  (lambda (f) (lambda (x) (f ((n f) x)))))
(define one (lambda (f) (lambda (x) (f x))))
(define two (lambda (f) (lambda (x) (f (f x)))))
(define (church-add a b)
    (lambda (f) (lambda (x) ((a f) ((b f) x)))))

(define (inc a) (+ a 1))
(define (church-convert a) ((a inc) 0))
(display "zero = ") (display (church-convert zero)) (newline)
(display "one = ") (display (church-convert one)) (newline)
(display "two = ") (display (church-convert two)) (newline)
(display "one + zero = ") (display (church-convert (church-add one zero))) (newline)
(display "one + one = ") (display (church-convert (church-add one one))) (newline)
(display "one + two = ") (display (church-convert (church-add one two))) (newline)
(display "two + two = ") (display (church-convert (church-add two two))) (newline)
