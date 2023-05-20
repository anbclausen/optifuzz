type expr_p =
  {
    size_p : float;

    true_p : float;
    false_p : float;
    not_p : float;

    x_p : float;
    y_p : float;
    int_lit_p : float;
    neg_p : float;
    plus_p : float;
    minus_p : float;
    times_p : float;
    less_than_p : float;
    less_equal_p : float;
    greater_than_p : float;
    greater_equal_p : float;
    equal_p : float;
    not_equal_p : float;

    bitwise_and_p : float;
    bitwise_or_p : float;
    bitwise_complement_p : float;
    bitwise_xor_p : float;
    left_shift_p : float;
    right_shift_p : float;
  }

let bool_expr_p p = p.true_p +. p.false_p +. p.not_p +. 
                    p.less_than_p +. p.less_equal_p +.
                    p.greater_than_p +. p.greater_equal_p +. 
                    p.equal_p +. p.not_equal_p

let arith_expr_p p = p.x_p +. p.y_p +. p.int_lit_p +. 
                     p.neg_p +. p.plus_p +. 
                     p.minus_p +. p.times_p 

(** Normalizes a list of floats. *)
let normalize p =
  List.map (fun x -> x /. (List.fold_left (+.) 0.0 p)) p

(** Takes a Random state, a list of values, and a list of probabilities
    and returns a value from the list of values with the corresponding
    probability. *)
let choose state l p =
  let roll = Random.State.float state 1.0 in
  let rec choose' l p acc =
    match l, p with
    | [], [] -> failwith "choose: empty list"
    | [], _ -> failwith "choose: list and probability list have different lengths"
    | _, [] -> failwith "choose: list and probability list have different lengths"
    | x :: xs, y :: ys ->
      if roll < acc +. y then
        x
      else
        choose' xs ys (acc +. y) in
  choose' l p 0.0

let choose_normalized state l p =
  choose state l (normalize p)

(** Generates a random AST. *)

(** Generates a random distribution of nodes in the AST. *)
let random_distribution seed =
  let state = Random.State.make [|seed|] in
  let random_arr = Array.init 23 (fun _ -> Random.State.float state 1.0) in
  let normalized_arr = Array.map (fun x -> x /. (Array.fold_left (+.) 0.0 random_arr)) random_arr in
  {
    size_p = normalized_arr.(0);
    
    true_p = normalized_arr.(1);
    false_p = normalized_arr.(2);
    not_p = normalized_arr.(3);

    x_p = normalized_arr.(4);
    y_p = normalized_arr.(5);
    int_lit_p = normalized_arr.(6);
    neg_p = normalized_arr.(7);
    plus_p = normalized_arr.(8);
    minus_p = normalized_arr.(9);
    times_p = normalized_arr.(10);
    less_than_p = normalized_arr.(11);
    less_equal_p = normalized_arr.(12);
    greater_than_p = normalized_arr.(13);
    greater_equal_p = normalized_arr.(14);
    equal_p = normalized_arr.(15);
    not_equal_p = normalized_arr.(16);

    bitwise_and_p = normalized_arr.(17);
    bitwise_or_p = normalized_arr.(18);
    bitwise_complement_p = normalized_arr.(19);
    bitwise_xor_p = normalized_arr.(20);
    left_shift_p = normalized_arr.(21);
    right_shift_p = normalized_arr.(22);
  }