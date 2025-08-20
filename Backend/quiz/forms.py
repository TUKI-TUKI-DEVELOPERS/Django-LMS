from django import forms
from django.forms.widgets import RadioSelect, Textarea
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from django.forms.models import inlineformset_factory

from accounts.models import User
from .models import Question, Quiz, MCQuestion, Choice


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_choices_list()]
        self.fields["answers"] = forms.ChoiceField(
            choices=choice_list, widget=RadioSelect
        )


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={"style": "width:100%"})
        )


class QuizAddForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("Questions"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAddForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields[
                "questions"
            ].initial = self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class MCQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQuestion
        exclude = ()


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["choice", "correct"]


class MCQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom validation for the formset to ensure:
        1. At least two choices are provided and not marked for deletion.
        2. At least one of the choices is marked as correct.
        """
        super().clean()

        # Collect non-deleted forms that have content
        valid_forms = []
        for form in self.forms:
            # Check if form is not marked for deletion
            if not form.cleaned_data.get('DELETE', True):
                # Check if choice field has content
                choice_content = form.cleaned_data.get('choice', '')
                if choice_content and choice_content.strip():  # Only count forms with actual content
                    valid_forms.append(form)

        # If we have less than 2 valid forms with content, raise error
        if len(valid_forms) < 2:
            raise forms.ValidationError("Debes proporcionar al menos dos opciones.")

        # Check if at least one of the valid forms is marked as correct
        correct_choices = [form.cleaned_data.get('correct', False) for form in valid_forms]

        if not any(correct_choices):
            raise forms.ValidationError("Una opción debe estar marcada como correcta.")
        
        if correct_choices.count(True) > 1:
            raise forms.ValidationError("Solo una opción debe estar marcada como correcta.")


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=ChoiceForm,
    formset=MCQuestionFormSet,
    fields=["choice", "correct"],
    can_delete=True,
    extra=10,  # Aumentamos de 5 a 10 opciones extra
    max_num=15,  # Máximo 15 opciones
)
