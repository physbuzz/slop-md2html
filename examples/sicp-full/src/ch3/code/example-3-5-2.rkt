#lang sicp

(define str (cons 1 (delay 2)))

(car str)

(force (cdr str))

;; This gives an error:
;; ((cdr str))

(define (stream-car stream) 
  (car stream))
(define (stream-cdr stream) 
  (force (cdr stream)))
(stream-car (cons-stream 1 2))
(stream-cdr (cons-stream 1 2))
