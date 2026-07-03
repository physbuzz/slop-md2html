#lang sicp

(define (stream-car stream) 
  (car stream))
(define (stream-cdr stream) 
  (force (cdr stream)))
(define (display-line x)
  (newline)
  (display x))
(define (stream-ref s n)
  (if (= n 0)
      (stream-car s)
      (stream-ref (stream-cdr s) (- n 1))))

(define (stream-map proc . argstreams)
  (if (stream-null? (car argstreams))
      the-empty-stream
      (cons-stream
       (apply proc (map stream-car argstreams))
       (apply stream-map (cons proc (map stream-cdr argstreams))))))
(define (add-streams s1 s2)
  (stream-map + s1 s2))
(define s (cons-stream 1 (add-streams s s)))


(display-line (stream-ref s 0))
(display-line (stream-ref s 1))
(display-line (stream-ref s 2))
(display-line (stream-ref s 3))
(display-line (stream-ref s 4))
(display-line (stream-ref s 5))
