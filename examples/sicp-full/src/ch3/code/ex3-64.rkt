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

(define (integers-starting-from n)
  (cons-stream 
   n (integers-starting-from (+ n 1))))
(define integers (integers-starting-from 1))
(define (stream-map proc . argstreams)
  (if (stream-null? (car argstreams))
      the-empty-stream
      (cons-stream
       (apply proc (map stream-car argstreams))
       (apply stream-map (cons proc (map stream-cdr argstreams))))))


(define (average a b) (/ (+ a b) 2))
(define (sqrt-improve guess x)
  (average guess (/ x guess)))
(define (sqrt-stream x)
  (define guesses
    (cons-stream 
     1.0 (stream-map
          (lambda (guess)
            (sqrt-improve guess x))
          guesses)))
  guesses)

(define (stream-limit stream tol)
  (define (iter str last-elem)
    (let ((this-elem (stream-car str)))
      (if (< (abs (- this-elem last-elem)) tol) this-elem
        (iter (stream-cdr str) this-elem))))
  (iter (stream-cdr stream) (stream-car stream)))
(define (sqrt x tolerance)
  (stream-limit (sqrt-stream x) tolerance))

(display-line "Series for tan(x)")
(display-line (sqrt 2.0 0.1))
(display-line (sqrt 2.0 0.0001))
(display-line (sqrt 2.0 0.00000001))
