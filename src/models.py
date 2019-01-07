import tensorflow as tf
from tensorflow.contrib.framework.python.ops import arg_scope
import nn
import tensorflow.contrib.layers as ly

### Added for CIS680 ###
def lrelu(x, leak=0.3, name="lrelu"):
    with tf.variable_scope(name):
        f1 = 0.5 * (1 + leak)
        f2 = 0.5 * (1 - leak)
        return f1 * x + f2 * abs(x)

def DiscriminatorNet(img, reuse=False):
    with tf.variable_scope('discriminator', reuse=tf.AUTO_REUSE) as scope:
#         if reuse:
#             scope.reuse_variables()
        size = 64
        img = ly.conv2d(img, num_outputs=size, kernel_size=3,
                        stride=2, activation_fn=lrelu)
        img = ly.conv2d(img, num_outputs=size * 2, kernel_size=3,
                        stride=2, activation_fn=lrelu, normalizer_fn=ly.batch_norm)
        img = ly.conv2d(img, num_outputs=size * 4, kernel_size=3,
                        stride=2, activation_fn=lrelu, normalizer_fn=ly.batch_norm)
        img = ly.conv2d(img, num_outputs=size * 8, kernel_size=3,
                        stride=2, activation_fn=lrelu, normalizer_fn=ly.batch_norm)
        logit = ly.fully_connected(tf.reshape(
            img, [8, -1]), 1, activation_fn=None) # 8 is the batch size here
    return logit
### CIS680 code ends ###

def model_arg_scope(**kwargs):
    """Create new counter and apply arg scope to all arg scoped nn
    operations."""
    counters = {}
    return arg_scope(
            [nn.conv2d, nn.deconv2d, nn.residual_block, nn.dense, nn.activate],
            counters = counters, **kwargs)


def make_model(name, template, **kwargs):
    """Create model with fixed kwargs."""
    run = lambda *args, **kw: template(*args, **dict((k, v) for kws in (kw, kwargs) for k, v in kws.items()))
    return tf.make_template(name, run, unique_name_ = name)


def dec_up(
        c, init = False, dropout_p = 0.5,
        n_scales = 1, n_residual_blocks = 2, activation = "elu", n_filters = 64, max_filters = 128):
    with model_arg_scope(
            init = init, dropout_p = dropout_p, activation = activation):
        # outputs
        hs = []
        # prepare input
        h = nn.nin(c, n_filters)
        for l in range(n_scales):
            # level module
            for i in range(n_residual_blocks):
                h = nn.residual_block(h)
                hs.append(h)
            # prepare input to next level
            if l + 1 < n_scales:
                n_filters = min(2*n_filters, max_filters)
                h = nn.downsample(h, n_filters)
        return hs


def dec_down(
        gs, zs_posterior, training, init = False, dropout_p = 0.5,
        n_scales = 1, n_residual_blocks = 2, activation = "elu",
        n_latent_scales = 2):
    assert n_residual_blocks % 2 == 0
    gs = list(gs)
    zs_posterior = list(zs_posterior)
    with model_arg_scope(
            init = init, dropout_p = dropout_p, activation = activation):
        # outputs
        hs = [] # hidden units
        ps = [] # priors
        zs = [] # prior samples
        # prepare input
        n_filters = gs[-1].shape.as_list()[-1]
        h = nn.nin(gs[-1], n_filters)
        for l in range(n_scales):
            # level module
            ## hidden units
            for i in range(n_residual_blocks // 2):
                h = nn.residual_block(h, gs.pop())
                hs.append(h)
            if l < n_latent_scales:
                ## prior
                spatial_shape = h.shape.as_list()[1]
                n_h_channels = h.shape.as_list()[-1]
                if spatial_shape == 1:
                    ### no spatial correlations
                    p = latent_parameters(h)
                    ps.append(p)
                    z_prior = latent_sample(p)
                    zs.append(z_prior)
                else:
                    ### four autoregressively modeled groups
                    if training:
                        z_posterior_groups = nn.split_groups(zs_posterior[0])
                    p_groups = []
                    z_groups = []
                    p_features = tf.space_to_depth(nn.residual_block(h), 2)
                    for i in range(4):
                        p_group = latent_parameters(p_features, num_filters = n_h_channels)
                        p_groups.append(p_group)
                        z_group = latent_sample(p_group)
                        z_groups.append(z_group)
                        # ar feedback sampled from
                        if training:
                            feedback = z_posterior_groups.pop(0)
                        else:
                            feedback = z_group
                        # prepare input for next group
                        if i + 1 < 4:
                            p_features = nn.residual_block(p_features, feedback)
                    if training:
                        assert not z_posterior_groups
                    # complete prior parameters
                    p = nn.merge_groups(p_groups)
                    ps.append(p)
                    # complete prior sample
                    z_prior = nn.merge_groups(z_groups)
                    zs.append(z_prior)
                ## vae feedback sampled from
                if training:
                    ## posterior
                    z = zs_posterior.pop(0)
                else:
                    ## prior
                    z = z_prior
                for i in range(n_residual_blocks // 2):
                    n_h_channels = h.shape.as_list()[-1]
                    h = tf.concat([h, z], axis = -1)
                    h = nn.nin(h, n_h_channels)
                    h = nn.residual_block(h, gs.pop())
                    hs.append(h)
            else:
                for i in range(n_residual_blocks // 2):
                    h = nn.residual_block(h, gs.pop())
                    hs.append(h)
            # prepare input to next level
            if l + 1 < n_scales:
                n_filters = gs[-1].shape.as_list()[-1]
                h = nn.upsample(h, n_filters)

        assert not gs
        if training:
            assert not zs_posterior

        return hs, ps, zs


def enc_up(
        x, c, init = False, dropout_p = 0.5,
        n_scales = 1, n_residual_blocks = 2, activation = "elu", n_filters = 64, max_filters = 128):
    with model_arg_scope(
            init = init, dropout_p = dropout_p, activation = activation):
        # outputs
        hs = []
        # prepare input
        #xc = tf.concat([x,c], axis = -1)
        xc = x
        h = nn.nin(xc, n_filters)
        for l in range(n_scales):
            # level module
            for i in range(n_residual_blocks):
                h = nn.residual_block(h)
                hs.append(h)
            # prepare input to next level
            if l + 1 < n_scales:
                n_filters = min(2*n_filters, max_filters)
                h = nn.downsample(h, n_filters)
        return hs


def enc_down(
        gs, init = False, dropout_p = 0.5,
        n_scales = 1, n_residual_blocks = 2, activation = "elu",
        n_latent_scales = 2):
    assert n_residual_blocks % 2 == 0
    gs = list(gs)
    with model_arg_scope(
            init = init, dropout_p = dropout_p, activation = activation):
        # outputs
        hs = [] # hidden units
        qs = [] # posteriors
        zs = [] # samples from posterior
        # prepare input
        n_filters = gs[-1].shape.as_list()[-1]
        h = nn.nin(gs[-1], n_filters)
        for l in range(n_scales):
            # level module
            ## hidden units
            for i in range(n_residual_blocks // 2):
                h = nn.residual_block(h, gs.pop())
                hs.append(h)
            if l < n_latent_scales:
                ## posterior parameters
                q = latent_parameters(h)
                qs.append(q)
                ## posterior sample
                z = latent_sample(q)
                zs.append(z)
                ## sample feedback
                for i in range(n_residual_blocks // 2):
                    gz = tf.concat([gs.pop(), z], axis = -1)
                    h = nn.residual_block(h, gz)
                    hs.append(h)
            else:
                break
            # prepare input to next level
            if l + 1 < n_scales:
                n_filters = gs[-1].shape.as_list()[-1]
                h = nn.upsample(h, n_filters)

        return hs, qs, zs


def dec_parameters(
        h, init = False, **kwargs):
    with model_arg_scope(init = init):
        num_filters = 3
        return nn.conv2d(h, num_filters)


def latent_parameters(
        h, init = False, **kwargs):
    num_filters = kwargs.get("num_filters", h.shape.as_list()[-1])
    return nn.conv2d(h, num_filters)


def latent_sample(p):
    mean = p
    stddev = 1.0
    eps = tf.random_normal(mean.shape, mean = 0.0, stddev = 1.0)
    return mean + stddev * eps


def latent_kl(q, p):
    mean1 = q
    mean2 = p

    kl = 0.5 * tf.square(mean2 - mean1)
    kl = tf.reduce_sum(kl, axis = [1,2,3])
    kl = tf.reduce_mean(kl)
    return kl
