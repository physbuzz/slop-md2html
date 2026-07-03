#lang sicp

(define (lookup key table)
  (let ((record (assoc key (cdr table))))
    (if record
        (cdr record)
        false)))

(define (assoc key records)
  (cond ((null? records) false)
        ((equal? key (caar records))
         (car records))
        (else (assoc key (cdr records)))))

(define (assoc-custom same-key? key records)
  (cond ((null? records) false)
        ((same-key? key (caar records))
         (car records))
        (else (assoc-custom same-key? key (cdr records)))))

(define (make-table same-key?)
  (let ((local-table (list '*table*)))
    (define (lookup key-1 key-2)
      (let ((subtable
             (assoc-custom same-key? key-1 (cdr local-table))))
        (if subtable
            (let ((record
                   (assoc-custom same-key? key-2
                          (cdr subtable))))
              (if record (cdr record) false))
            false)))
    (define (insert! key-1 key-2 value)
      (let ((subtable
             (assoc-custom same-key? key-1 (cdr local-table))))
        (if subtable
            (let ((record
                   (assoc-custom same-key? key-2
                          (cdr subtable))))
              (if record
                  (set-cdr! record value)
                  (set-cdr!
                   subtable
                   (cons (cons key-2 value)
                         (cdr subtable)))))
            (set-cdr!
             local-table
             (cons (list key-1
                         (cons key-2 value))
                   (cdr local-table)))))
      'ok)
    (define (dispatch m)
      (cond ((eq? m 'lookup-proc) lookup)
            ((eq? m 'insert-proc!) insert!)
            (else (error "Unknown operation:
                          TABLE" m))))
    dispatch))


(define (fuzzy-equals? a b)
  (< (abs (- b a)) 0.05))

(define operation-table (make-table fuzzy-equals?))
(define get (operation-table 'lookup-proc))
(define put (operation-table 'insert-proc!))

(put 1 0.1 'a)
(put 1 0.3 'b)
(display (get 1 0.13)) (newline)
(display (get 1 0.2)) (newline)
(display (get 1 0.26))





