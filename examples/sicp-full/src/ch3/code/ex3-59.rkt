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

(define (negate-series S) (stream-map - S))

(define (integrate-series S)
  (stream-map / S integers))

(define exp-series
  (cons-stream
   1 (integrate-series exp-series)))
(display-line "Part 1, exp series:")
(display-stream-first-n exp-series 6)

(define cosine-series
  (cons-stream 1 (integrate-series (negate-series sine-series))))
(define sine-series
  (cons-stream 0 (integrate-series cosine-series)))

(display-line "Part 2, sine series:")

(display-stream-first-n sine-series 6)
(display-line "Part 2, cosine series:")
(display-stream-first-n cosine-series 6)


