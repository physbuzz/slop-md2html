#lang sicp

(define (stream-car stream) 
  (car stream))
(define (stream-cdr stream) 
  (force (cdr stream)))
(define (display-stream-first-n s n)
  (if (and (not (stream-null? s)) (> n 0))
    (begin 
      (display-line (stream-car s))
      (display-stream-first-n (stream-cdr s) (- n 1)))))
(define (display-line x)
  (newline)
  (display x))


(define pluscount 0)
(define (+new a b) 
  (begin (set! pluscount (+ pluscount 1))
         (+ a b)))

(define (fibgen a b)
  (cons-stream a (fibgen b (+new a b))))

(define fibs (fibgen 0 1))

(display-stream-first-n fibs 10)
(display pluscount)
