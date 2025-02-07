from oscar.core.loading import get_model

WishList = get_model("wishlists", "WishList")


# class WishListLineForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
