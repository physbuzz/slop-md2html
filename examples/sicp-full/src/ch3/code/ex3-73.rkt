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
(define (constant-stream val)
  (cons-stream val (constant-stream val)))

(define (square x) (* x x))
(define (negate-series S) (stream-map - S))
(define (add-streams s1 s2)
  (stream-map + s1 s2))
(define (mul-streams s1 s2)
  (stream-map * s1 s2))
(define (scale-stream S m) 
  (stream-map (lambda (x) (* x m)) S))
(define (mul-series s1 s2)
  (add-streams 
    (scale-stream s2 (stream-car s1))
    (cons-stream 0 (mul-series (stream-cdr s1) s2))))
(define (partial-sums s)
  (cons-stream 0
    (add-streams s (partial-sums s))))

(define (stream-ref s n)
  (if (= n 0)
      (stream-car s)
      (stream-ref (stream-cdr s) (- n 1))))

(define (integral integrand initial-value dt)
  (define int
    (cons-stream
     initial-value
     (add-streams (scale-stream integrand dt)
                  int)))
  int)
(define (RC R C dt)
  (lambda (i v0)
    (let ((cap-voltage 
        (stream-map (lambda (x) (+ x v0)) (scale-stream (integral i 0 dt) (/ 1.0 C))))
          (resistor-voltage (scale-stream i R)))
      (add-streams cap-voltage resistor-voltage))))


(define RC1 (RC 5 1 0.5))
(display-stream-first-n (RC1 (constant-stream 1) 1.0) 10)
