#lang sicp

(define (front-ptr deque) (car deque))
(define (rear-ptr deque) (cdr deque))
(define (set-front-ptr! deque item) (set-car! deque item))
(define (set-rear-ptr! deque item) (set-cdr! deque item))
(define (empty-deque? deque) (null? (front-ptr deque)))
(define (make-deque) (cons '() '()))

;; Gets the first value in the deque
(define (front-deque deque)
  (if (empty-deque? deque)
      (error "FRONT called with an
              empty deque" deque)
      (car (front-ptr deque))))

;; Gets the last value in the deque
(define (rear-deque deque)
  (if (empty-deque? deque)
      (error "REAR called with an
              empty deque" deque)
      (car (rear-ptr deque))))

(define (rear-insert-deque! deque item)
  ;;cf ((new-pair (cons item '())))
  (let ((new-pair (cons (list item '()) '())))
    (cond ((empty-deque? deque)
           (set-front-ptr! deque new-pair)
           (set-rear-ptr! deque new-pair)
           deque)
          (else 
              ;; 1. Update the new-pair's prev-ptr
              (set-car! (cdar new-pair) (rear-ptr deque))
              ;; 2. Add it to the end of the list
              (set-cdr! (rear-ptr deque) new-pair)
              ;; 3. Update rear-ptr.
              (set-rear-ptr! deque new-pair)
              deque))))


(define (rear-delete-deque! deque)
  (cond ((empty-deque? deque)
         (error "REAR-DELETE! called with 
                 an empty deque" deque))
        (else 
          ;; 1. Save the value of the prev-ptr
          (let ((prev-ptr (cadr (rear-deque deque))))
            ;; 2. If the prev ptr is null, set the queue to null
            (if (null? prev-ptr) 
              (begin 
                (set-front-ptr! deque '())
                (set-rear-ptr! deque '()))
              ;; 3. Else, chop the list off and move
              ;; rear-ptr back one.
              (begin
                (set-cdr! prev-ptr '())
                (set-rear-ptr! deque prev-ptr)))
            deque))))

(define (front-insert-deque! deque item)
  (let ((new-pair (cons (list item '()) (front-ptr deque))))
    (cond ((empty-deque? deque)
           (set-front-ptr! deque new-pair)
           (set-rear-ptr! deque new-pair)
           deque)
          (else (set-front-ptr! deque new-pair)
                deque))))

(define (front-delete-deque! deque)
  (cond ((empty-deque? deque)
         (error "DELETE! called with 
                 an empty deque" deque))
        (else (set-front-ptr! deque (cdr (front-ptr deque)))
              (if (not (null? (front-ptr deque)))
                ;; Update the first element's prev-ptr to null
                (set-car! (cdar (front-ptr deque)) '()))
              deque)))

(define (print-deque deque)
  (define (print-deque-inner lst)
    (cond ((null? lst) (display ")"))
          ((null? (cdr lst))
            (display (caar lst)) (display ")"))
          (else (display (caar lst)) 
             (display " ")
             (print-deque-inner (cdr lst)))))
  (display "(")
  (print-deque-inner (front-ptr deque)) (newline))

(define q1 (make-deque))

(print-deque (rear-insert-deque! q1 'c))
(print-deque (rear-insert-deque! q1 'd))
(print-deque (rear-insert-deque! q1 'e))
(print-deque (front-delete-deque! q1))
(print-deque (front-insert-deque! q1 'b))
(print-deque (front-insert-deque! q1 'a))
(print-deque (rear-delete-deque! q1))
(print-deque (rear-insert-deque! q1 'f))
(print-deque (rear-delete-deque! q1))
(print-deque (front-delete-deque! q1))
(print-deque (front-delete-deque! q1))
(print-deque (rear-delete-deque! q1))

