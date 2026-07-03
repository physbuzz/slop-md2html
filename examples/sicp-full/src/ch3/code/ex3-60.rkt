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
(define cosine-series
  (cons-stream 1 (integrate-series (negate-series sine-series))))
(define sine-series
  (cons-stream 0 (integrate-series cosine-series)))




(define (add-streams s1 s2)
  (stream-map + s1 s2))
(define (mul-streams s1 s2)
  (stream-map * s1 s2))
(define (scale-stream S m) 
  (stream-map (lambda (x) (* x m)) S))
;(define (mul-series s1 s2)
;  (cons-stream 
;    (* (stream-car s1) (stream-car s2))
;    (add-streams 
;      (scale-stream (stream-cdr s2) (stream-car s1))
;      (mul-series (stream-cdr s1) s2))))
(define (mul-series s1 s2)
  (add-streams 
    (scale-stream s2 (stream-car s1))
    (cons-stream 0 (mul-series (stream-cdr s1) s2))))

(define sum-squared-stream
  (add-streams (mul-series sine-series sine-series)
               (mul-series cosine-series cosine-series)))

(display-line "cos^2+sin^2 series:")
(display-stream-first-n sum-squared-stream 8)

