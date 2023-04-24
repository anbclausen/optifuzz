open Ast
open Generator

let () = 
  Random.self_init ();
  let seed = Random.bits () in
  print_endline ("SEED: " ^ string_of_int seed);
  let distribution = 
    {
      neg_p = 1. /. 24.;
      plus_p = 1. /. 24.;
      minus_p = 1. /. 24.;
      times_p = 1. /. 24.;
      div_p = 1. /. 24.;
      mod_p = 1. /. 24.;
      less_than_p = 1. /. 24.;
      less_equal_p = 1. /. 24.;
      greater_than_p = 1. /. 24.;
      greater_equal_p = 1. /. 24.;
      equal_p = 1. /. 24.;
      not_equal_p = 1. /. 24.;

      logical_and_p = 1. /. 24.;
      logical_or_p = 1. /. 24.;
      not_p = 1. /. 24.;

      bitwise_and_p = 1. /. 24.;
      bitwise_or_p = 1. /. 24.;
      bitwise_complement_p = 1. /. 24.;
      bitwise_xor_p = 1. /. 24.;
      left_shift_p = 1. /. 24.;
      right_shift_p = 1. /. 24.;

      x_p = 1. /. 24.;
      y_p = 1. /. 24.;
      int_lit_p = 1. /. 24.;
    } in
  print_endline (string_of_expr (random_ast seed 0 distribution))