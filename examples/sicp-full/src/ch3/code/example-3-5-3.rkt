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

(define (display-line x)
  (newline)
  (display x))

(display-stream (stream-enumerate-interval 1 6))


(define (stream-ref s n)
  (if (= n 0)
      (stream-car s)
      (stream-ref (stream-cdr s) (- n 1))))

(define (stream-map proc s)
  (if (stream-null? s)
      the-empty-stream
      (cons-stream
       (proc (stream-car s))
       (stream-map proc (stream-cdr s)))))


;; (stream-car 
;;  (stream-cdr
;;   (stream-filter 
;;    prime? (stream-enumerate-interval 
;;            10000 1000000))))

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


(define (stream-map proc . argstreams)
  (if (⟨??⟩ (car argstreams))
      the-empty-stream
      (⟨??⟩
       (apply proc (map ⟨??⟩ argstreams))
       (apply stream-map
              (cons proc
                    (map ⟨??⟩
                         argstreams))))))
