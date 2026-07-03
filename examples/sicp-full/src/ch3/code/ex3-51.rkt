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
         (stream-enumerate-odds (+ low 1) high))
        (else
         (cons-stream
          low
          (stream-enumerate-odds (+ low 2)
                                     high)))))
(define (stream-enumerate-evens low high)
  (cond ((> low high) the-empty-stream)
        ((= (remainder low 2) 1)
         (stream-enumerate-evens (+ low 1) high))
        (else
         (cons-stream
          low
          (stream-enumerate-evens (+ low 2)
                                     high)))))
(define (stream-enumerate-constant c n)
  (if (= n 0) 
    the-empty-stream
    (cons-stream
     c
     (stream-enumerate-constant c (- n 1)))))

(define (stream-for-each proc s)
  (if (stream-null? s)
      'done
      (begin
        (proc (stream-car s))
        (stream-for-each proc
                         (stream-cdr s)))))

(define (display-stream s)
  (stream-for-each display-line s))

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

; (display-stream (stream-enumerate-evens 1 6))
; (display-stream (stream-enumerate-odds 1 6))
; (display-stream (stream-enumerate-constant 1/2 6))


(define (show x)
  (display-line x)
  x)

(define x
  (stream-map
   show
   (stream-enumerate-interval 0 10)))
; 0

(stream-ref x 5)
; 1
; 2
; 3
; 4
; 5 <- from (newline) (display 5)
; 5 <- from the output of the function
(stream-ref x 7)
; 6
; 7 <- from (newline) (display 5)
; 7 <- from the output of the function













