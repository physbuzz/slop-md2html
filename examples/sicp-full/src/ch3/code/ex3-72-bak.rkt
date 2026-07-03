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



(define (interleave s1 s2)
  (if (stream-null? s1)
      s2
      (cons-stream
       (stream-car s1)
       (interleave s2 (stream-cdr s1)))))

(define (merge s1 s2)
  (cond ((stream-null? s1) s2)
        ((stream-null? s2) s1)
        (else
         (let ((s1car (stream-car s1))
               (s2car (stream-car s2)))
           (cond ((< s1car s2car)
                  (cons-stream 
                   s1car 
                   (merge (stream-cdr s1) 
                          s2)))
                 ((> s1car s2car)
                  (cons-stream 
                   s2car 
                   (merge s1 
                          (stream-cdr s2))))
                 (else
                  (cons-stream 
                   s1car
                   (merge 
                    (stream-cdr s1)
                    (stream-cdr s2)))))))))

(define (merge-weighted s1 s2 W)
  (cond ((stream-null? s1) s2)
        ((stream-null? s2) s1)
        (else
         (let ((s1car (stream-car s1))
               (s2car (stream-car s2)))
           (cond ((<= (W s1car) (W s2car))
                  (cons-stream 
                   s1car 
                   (merge-weighted (stream-cdr s1) 
                                   s2 
                                   W)))
                 (else
                  (cons-stream 
                   s2car 
                   (merge-weighted s1 
                                   (stream-cdr s2)
                                   W))))))))

(define (weighted-pairs s t W)
  (cons-stream
   (list (stream-car s) (stream-car t))
   (merge-weighted
    (stream-map (lambda (x)
                  (list (stream-car s) x))
                (stream-cdr t))
    (weighted-pairs (stream-cdr s) (stream-cdr t) W) 
    W)))

(define (pairs s t)
  (cons-stream
   (list (stream-car s) (stream-car t))
   (interleave
    (stream-map (lambda (x)
                  (list (stream-car s) x))
                (stream-cdr t))
    (pairs (stream-cdr s) (stream-cdr t)))))

(define (stream-filter pred stream)
  (cond ((stream-null? stream)
         the-empty-stream)
        ((pred (stream-car stream))
         (cons-stream
          (stream-car stream)
          (stream-filter
           pred
           (stream-cdr stream))))
        (else (stream-filter
               pred
               (stream-cdr stream)))))

(define (my-W x) 
  (let ((i (car x)) (j (cadr x))) 
    (+ (square i) (square j))))
(define square-sorted-stream 
  (weighted-pairs integers integers my-W))

(define (my-search s lv llv n)
  (if (> n 0)
    (let ((nv (stream-car s)))
      (if (and (= (my-W nv) (my-W lv))
               (= (my-W lv) (my-W llv)))
        (begin 
          (display "Found: ")
          (display nv)
          (display ", ")
          (display lv)
          (display ", ")
          (display llv)
          (display " with sum squares ")
          (display (my-W lv)) (newline)
          (my-search (stream-cdr s) nv lv (- n 1)))
        (my-search (stream-cdr s) nv lv n)))))

(my-search square-sorted-stream (list 0 0) (list 0 0) 6)

; (define echo (lambda (x) (begin 
;    (display-line (my-W x)) x)))
; (display-stream-first-n 
;  (stream-map echo cube-sorted-stream) 100)















