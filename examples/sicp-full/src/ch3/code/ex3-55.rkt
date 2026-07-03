#lang sicp

(define (stream-car stream) 
  (car stream))
(define (stream-cdr stream) 
  (force (cdr stream)))

(define (stream-enumerate-interval low high)
  (if (> low high)
      the-empty-stream
      (cons-stream
       low
       (stream-enumerate-interval (+ low 1)
                                  high))))
(define (stream-enumerate-odds low high)
  (cond ((> low high) the-empty-stream)
        ((= (remainder low 2) 0)
         (stream-enumerate-interval (+ low 1) high))
        (else
         (cons-stream
          low
          (stream-enumerate-interval (+ low 2)
                                     high)))))
(define (stream-enumerate-evens low high)
  (cond ((> low high) the-empty-stream)
        ((= (remainder low 2) 1)
         (stream-enumerate-interval (+ low 1) high))
        (else
         (cons-stream
          low
          (stream-enumerate-interval (+ low 2)
                                     high)))))

(define (stream-for-each proc s)
  (if (stream-null? s)
      'done
      (begin
        (proc (stream-car s))
        (stream-for-each proc
                         (stream-cdr s)))))

(define (display-stream s)
  (stream-for-each display-line s))

(define (display-stream-first-n s n)
  (if (and (not (stream-null? s)) (> n 0))
    (begin 
      (display-line (stream-car s))
      (display-stream-first-n (stream-cdr s) (- n 1)))))

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
(define (add-streams s1 s2)
  (stream-map + s1 s2))
(define (mul-streams s1 s2)
  (stream-map * s1 s2))

(define (integers-starting-from n)
  (cons-stream 
   n (integers-starting-from (+ n 1))))
(define integers (integers-starting-from 1))
(define (partial-sums s)
  (cons-stream 0
    (add-streams s (partial-sums s))))
(display-stream-first-n (partial-sums integers) 10)
