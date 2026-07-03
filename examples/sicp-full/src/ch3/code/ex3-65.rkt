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


(define (euler-transform s)
  (let ((s0 (stream-ref s 0))     ; Sₙ₋₁
        (s1 (stream-ref s 1))     ; Sₙ
        (s2 (stream-ref s 2)))    ; Sₙ₊₁
    (cons-stream 
     (- s2 (/ (square (- s2 s1))
              (+ s0 (* -2 s1) s2)))
     (euler-transform (stream-cdr s)))))
(define (make-tableau transform s)
  (cons-stream
   s
   (make-tableau
    transform
    (transform s))))
(define (accelerated-sequence transform s)
  (stream-map stream-car
              (make-tableau transform s)))

(define (ln2-summands n)
  (cons-stream 
   (/ 1.0 n)
   (stream-map - (ln2-summands (+ n 1)))))
(define ln2-stream
  (partial-sums (ln2-summands 1)))
(display-line "Unaccelerated ln2-stream")
(display-stream-first-n ln2-stream 7)
(display-line "Euler transform ln2-stream")
(display-stream-first-n (euler-transform ln2-stream) 7)
(display-line "Euler transform + tableau ln2-stream")
(display-stream-first-n (accelerated-sequence euler-transform ln2-stream) 7)

