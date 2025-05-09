from typing import Callable, Iterable, Tuple

import torch
from torch.optim import Optimizer


class AdamW(Optimizer):
    def __init__(
            self,
            params: Iterable[torch.nn.parameter.Parameter],
            lr: float = 1e-3,
            betas: Tuple[float, float] = (0.9, 0.999),
            eps: float = 1e-6,
            weight_decay: float = 0.0,
            correct_bias: bool = True,
            max_grad_norm: float = None,
    ):
        if lr < 0.0:
            raise ValueError("Invalid learning rate: {} - should be >= 0.0".format(lr))
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[0]))
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[1]))
        if not 0.0 <= eps:
            raise ValueError("Invalid epsilon value: {} - should be >= 0.0".format(eps))
        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay, correct_bias=correct_bias, max_grad_norm=max_grad_norm)
        super().__init__(params, defaults)

    def step(self, closure: Callable = None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:

            # TODO: Clip gradients if max_grad_norm is set
            if group['max_grad_norm'] is not None:
                # raise NotImplementedError()
                torch.nn.utils.clip_grad_norm_(group["params"], group['max_grad_norm'])
            
            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError("Adam does not support sparse gradients, please consider SparseAdam instead")

                # raise NotImplementedError()

                # State should be stored in this dictionary
                state = self.state[p]

                # TODO: Access hyperparameters from the `group` dictionary
                alpha = group["lr"]
                b1, b2 = group["betas"]
                eps = group["eps"]
                weight_decay = group["weight_decay"]
                correct_bias = group["correct_bias"]

                # TODO: Update first and second moments of the gradients
                if len(state) == 0:
                    state["avg_g"] = torch.zeros_like(p.data) # average of gradient
                    state["avg_sg"] = torch.zeros_like(p.data) # average of squared gradient
                    state["step"] = 0
                avg_g = state["avg_g"]
                avg_sg = state["avg_sg"]
                state["step"] += 1
                step = state["step"]
                avg_g.mul_(b1).add_(grad, alpha=1-b1)
                avg_sg.mul_(b2).addcmul_(grad, grad, value=1-b2)

                # TODO: Bias correction
                # Please note that we are using the "efficient version" given in
                # https://arxiv.org/abs/1412.6980
                # TODO: Update parameters
                if correct_bias: # with correction
                    p.data.addcdiv_(avg_g, (avg_sg.sqrt() / torch.sqrt(torch.tensor(1 - b2 ** step))).add_(eps), value=-alpha/(1-b1**step))
                else: # with no correction
                    p.data.addcdiv_(avg_g, avg_sg.sqrt().add_(eps), value=-alpha)
                
                # TODO: Add weight decay after the main gradient-based updates.
                # Please note that the learning rate should be incorporated into this update.
                if weight_decay != 0.0: p.mul_(1 - alpha * weight_decay)

        return loss
